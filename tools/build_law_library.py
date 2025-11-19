import os
import requests
import time

# ---------------------------------------------------------
# 1. BASE DIRECTORY FIX (Prevents data/data duplication)
# ---------------------------------------------------------

# Get absolute project root (folder where this script is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define correct data paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
POLICY_DIR = os.path.join(KNOWLEDGE_DIR, "policies")

# ---------------------------------------------------------
# 2. POLICY URLS
# ---------------------------------------------------------

POLICY_URLS = {
    "Star_Comprehensive_Policy_2024.pdf": "https://irdai.gov.in/documents/37343/931203/SHAHLIP22028V072122_HEALTH2050.pdf/70aade12-d528-1155-a8b7-c03d2cfecd15?version=1.1&download=true",
    "HDFC_ERGO_Optima_Restore.pdf": "https://algatesinsurance.in/resources/policy-documents/hdfc-ergo/optima-restore-policy-wordings.pdf",
    "Niva_Bupa_ReAssure_2.0.pdf": "https://transactions.nivabupa.com/pages/doc/policy_wording/ReAssure-2.0-Policy-Wording.pdf",
    "ICICI_Lombard_iHealth.pdf": "https://www.icicilombard.com/docs/default-source/policy-wordings-product-brochure/complete-health-insurance-(ihealth)-new.pdf",
    "Aditya_Birla_Activ_Health.pdf": "https://www.adityabirlacapital.com/healthinsurance/assets/pdf/policy-wording-form.pdf",
    "SBI_General_Arogya_Sanjeevani.pdf": "https://content.sbigeneral.in/uploads/e14cc6abce7d4f4a8e9d0f1cf6f212e8.pdf",
    "Tata_AIG_Medicare.pdf": "https://irdai.gov.in/documents/37343/931203/TATHLIP21225V022021_2020-2021.pdf/63626023-5d4a-32f7-2f30-0d58882c191c?version=1.1&download=true"
}

# ---------------------------------------------------------
# 3. STATUTES CONTENT
# ---------------------------------------------------------

STATUTES_CONTENT = """# INDIAN LEGAL KNOWLEDGE BASE (IRDAI, CPA & OMBUDSMAN)

## 1. CLAIM SETTLEMENT & INTEREST (The "30 Day" Rule)
IRDAI Regulations (2017) Reg 15(10):
- Insurer must settle or reject a claim within 30 days.
- Investigation max timeline = 45 days.
- Penalty interest = 2% above Bank Rate.

## 2. MORATORIUM PERIOD (5 Year Clause)
IRDAI Master Circular 2024 (Clause 4.2):
- After 60 months of coverage, claim cannot be rejected for non-disclosure unless fraud is proven.

## 3. CONSUMER PROTECTION ACT 2019
Wrongful claim denial = Deficiency in Service.

## 4. INSURANCE OMBUDSMAN RULES 2017
- Handles repudiation, delay, disputes.
- Limit: ₹30 Lakhs.
- Free, binding on insurer.

## 5. STANDARDIZATION OF EXCLUSIONS (2019)
- Mental Illness mandatory coverage.
- Modern treatments like Robotic Surgery must be covered.
"""

# ---------------------------------------------------------
# 4. DIRECTORY SETUP
# ---------------------------------------------------------

def setup_directories():
    os.makedirs(POLICY_DIR, exist_ok=True)
    print(f"📂 Using data directory: {DATA_DIR}")
    print(f"📚 Knowledge base: {KNOWLEDGE_DIR}")
    print(f"📄 Policies folder: {POLICY_DIR}")
    return KNOWLEDGE_DIR, POLICY_DIR

# ---------------------------------------------------------
# 5. FILE DOWNLOADER
# ---------------------------------------------------------

def download_file(url, filename, folder):
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"✔ Already exists: {filename}")
        return

    print(f"⬇️ Downloading: {filename}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=20)
        resp.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

        print(f"✅ Saved: {filename}")

    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")

# ---------------------------------------------------------
# 6. WRITE STATUTES
# ---------------------------------------------------------

def create_statutes_file(folder):
    filepath = os.path.join(folder, "statutes.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(STATUTES_CONTENT)
    print(f"📜 Created statutes.md at: {filepath}")

# ---------------------------------------------------------
# 7. MAIN EXECUTION
# ---------------------------------------------------------

def main():
    print("\n--- 🏛 BUILDING ADVOCAI LEGAL ENGINE (INDIA) ---\n")

    # Create directories
    knowledge_dir, policy_dir = setup_directories()

    # Save statutes
    create_statutes_file(knowledge_dir)

    print(f"\n--- 📥 DOWNLOADING {len(POLICY_URLS)} POLICY DOCUMENTS ---\n")

    for name, url in POLICY_URLS.items():
        download_file(url, name, policy_dir)
        time.sleep(1.5)

    print("\n🎉 LEGAL ENGINE READY!")
    print(f"📂 Policies → {policy_dir}")
    print(f"📜 Statutes → {os.path.join(knowledge_dir, 'statutes.md')}")
    print("\nYou can now run the Regulatory Agent.\n")

if __name__ == "__main__":
    main()
