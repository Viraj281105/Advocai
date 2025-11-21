Absolutely — here is your **final, clean, polished, copy-paste-ready `README.md`** exactly as requested.

You can paste this directly into GitHub.
Formatting, spacing, headers, markdown structure — all optimized for a professional open-source project.

---

# 🚀 Advocai — The Autonomous Health Insurance Advocate

> **Kaggle Agents Intensive — Capstone Project**
> **Track:** Agents for Good
> **Purpose:** Turn denied health insurance claims into evidence-backed appeal packages using a fully autonomous multi-agent workflow.

---

## 📌 Quick Overview

**Insurers deny claims using opaque algorithms.**
Patients, lacking legal or clinical expertise, rarely win appeals — leading to financial strain and emotional stress.

**Advocai** solves this by using a **sequential multi-agent system** that:

* Extracts denial codes and policy clauses
* Fetches authoritative medical evidence
* Generates a professionally structured legal appeal letter
* Outputs a complete submission-ready package

---

## 🧩 Features

* **Tri-Agent System:** Auditor → Clinician → Barrister
* **PDF/OCR ingestion** with robust error handling
* **Clinical evidence retrieval** (e.g., PubMed tool)
* **Legally structured appeal drafting**
* **Session memory** via `InMemorySessionService`
* **Configurable LLM backends** (Gemini supported for Kaggle bonus points)
* **Submission-ready output** (PDFs + metadata bundle)

---

## 🏗️ Architecture

```
Upload PDF → Auditor Agent → Session Storage
                         ↓
                  Clinician Agent
                         ↓
                  Barrister Agent
                         ↓
           Final Appeal Package (PDF + JSON)
```

### Agent Responsibilities

#### 🕵️ Auditor Agent

* OCR + text extraction
* Denial code identification
* Policy clause matching
* Outputs structured `AuditorReport`

#### 🩺 Clinician Agent

* Uses extracted denial info
* Queries medical evidence databases
* Produces `ClinicalDossier`

#### ⚖️ Barrister Agent

* Drafts legal appeal letter
* Builds evidence bundle
* Generates complete appeal package

---

## ⚙️ Installation & Quickstart

### 1. Clone Repository

```bash
git clone https://github.com/Viraj281105/Advocai.git
cd Advocai
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` in the project root:

```ini
GEMINI_API_KEY=your_key_here
PUBMED_API_KEY=optional_key
TESSERACT_CMD=/usr/bin/tesseract
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

### 5. Run Advocai

```bash
python main.py \
  --input path/to/denial_letter.pdf \
  --policy path/to/policy.pdf \
  --out ./output
```

---

## 🔧 Pipeline Flow (Step-by-Step)

1. **User uploads denial PDF**
2. **Auditor** performs OCR + structured extraction
3. **Session store** persists findings
4. **Clinician** retrieves clinical evidence
5. **Barrister** drafts legal appeal letter
6. **Final package** created (letter + evidence + metadata)

---

## 📦 Example Outputs

### AuditorReport (JSON)

```json
{
  "session_id": "2025-11-21-viraj",
  "claim_id": "CLM-00012345",
  "denial_code": "A35",
  "policy_clauses": [
    {
      "clause_id": "4.2",
      "text": "Coverage excludes experimental procedures unless..."
    }
  ],
  "provider": {
    "name": "Good Health Clinic",
    "npi": "1234567890"
  },
  "billed_codes": ["CPT 99214", "ICD-10 M54.5"],
  "confidence_scores": {
    "denial_code": 0.93,
    "policy_match": 0.81
  }
}
```

### Appeal Letter (Excerpt)

```
Re: Claim CLM-00012345 — Formal Appeal of Denial (A35)

To the Appeals Department,
This letter challenges the denial issued under code A35. According to policy section 4.2 and the clinical evidence (Smith et al., 2021; NICE, 2023), the treatment meets the criteria for medical necessity...
```

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit
```

### End-to-End Tests

```bash
pytest tests/e2e
```

Suggested evaluation metrics:

* Extraction accuracy (Auditor)
* Evidence relevance (Clinician)
* Legal argument quality (Barrister)
* Latency & performance

---

## 🔐 Security, Privacy & Compliance

* Denial PDFs often contain PHI — process locally where possible
* Enable encrypted storage
* Provide disclaimers: Advocai aids appeals but does *not* replace legal counsel
* Redaction recommended for cloud routes
* Logging excludes sensitive fields

---

## 📈 Limitations & Future Enhancements

### Current Limitations

* OCR quality sensitive to scan resolution
* PubMed API rate limits
* No built-in redaction module
* Context engineering + agent evaluation pending

### Future Improvements

* Better semantic search for policy clauses
* Fine-grained evaluation harness
* Cloud Run / Vertex AI deployment package
* Web dashboard for human-in-the-loop review

---

## 🗂️ Project Structure

```
Advocai/
├─ advocai/
│  ├─ agents/
│  │  ├─ auditor.py
│  │  ├─ clinician.py
│  │  └─ barrister.py
│  ├─ tools/
│  │  ├─ ocr.py
│  │  ├─ pubmed_client.py
│  │  └─ pdf_utils.py
│  ├─ services/
│  │  └─ in_memory_session.py
│  ├─ cli.py
│  └─ main.py
├─ tests/
├─ samples/
├─ requirements.txt
├─ README.md
└─ .env.example
```

---

## 👥 Team Advocai

| Role                  | Name       | Kaggle Username |
| --------------------- | ---------- | --------------- |
| Lead Developer        | Your Name  | your_kaggle     |
| Documentation & Pitch | Teammate 2 | user_2          |
| Clinical Agent Dev    | Teammate 3 | user_3          |
| Tools & Deployment    | Teammate 4 | user_4          |

---

## 🤝 Contribution Guide

1. Fork repository
2. Create feature branches
3. Use `black` + `ruff`
4. Update `.env.example` for new variables
5. Write tests for new modules
6. Open PRs with descriptive titles

---

## 📄 License

Released under the **MIT License**.

---

## 📌 Bonus Points (for Kaggle)

* [ ] Gemini usage
* [ ] Deployment demo (Cloud Run / Vertex AI)
* [ ] YouTube walkthrough video

---

If you want, I can also prepare:

✅ `.env.example`
✅ `Dockerfile`
✅ Sample denial PDF
✅ Sample policy PDF
✅ A full YouTube video script for your submission

Just tell me what you want next.
